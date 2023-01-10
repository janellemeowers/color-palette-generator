import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.pyplot
import io
import matplotlib.image as mpimg
from PIL import Image
import base64
#get rgb values
import extcolors
#convert to hex
from colormap import rgb2hex
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from flask import Flask, render_template, redirect, url_for, request
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = os.path.join('static', 'uploads')


global image_url, resize_name

app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SECRET_KEY'] = '8BYkEfBA6O8923jgljalsgjWIGJKLDSL81'

global df_color, photo, resize_name

@app.route("/", methods=['POST', 'GET'])
def home():
    global df_color, resize_name

    if request.method == 'POST':
        photo = request.files['image']
        #get file name
        img_filename = secure_filename(photo.filename)
        #save
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
        #save path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(photo.filename))


        img = Image.open(file_path)
        #resize image
        wpercent = (900/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((900,hsize), Image.ANTIALIAS)
        resize_name = 'resized_' + img_filename
        img.save(resize_name)

        # get RGB colors
        colors_x = extcolors.extract_from_path(resize_name, tolerance=12, limit=12)
        # prep for dataframe
        colors_pre_list = str(colors_x).replace('([(', '').split(', (')[0:-1]
        df_rgb = [i.split('), ')[0] + ')' for i in colors_pre_list]
        #gives you occurence num
        df_percent = [i.split('), ')[1].replace(')', '') for i in colors_pre_list]

        # convert RGB to HEX code (0, 1, 2,)
        df_color_up = [rgb2hex(int(i.split(", ")[0].replace("(", "")),
                               int(i.split(", ")[1]),
                               int(i.split(", ")[2].replace(")", ""))) for i in df_rgb]

        #zip together in DF
        df_color = pd.DataFrame(zip(df_color_up, df_percent), columns=['colors', 'occurrence'])
        return redirect(url_for('create_donut'))



    return render_template("index.html")


@app.route('/result', methods=['POST', 'GET'])
def create_donut():
    list_color = list(df_color['colors'])
    list_pcent = [int(i) for i in list(df_color['occurrence'])]
    #get % occurrence out of sum. display text #color + %
    text_c = [c + ' ' + str(round(p * 100 / sum(list_pcent), 1)) + '%' for c, p in zip(list_color,
                                                                                         list_pcent)]
    #do not create bg GUI
    matplotlib.pyplot.switch_backend('Agg')

    fig, ax1 = plt.subplots(figsize=(160,90), dpi = 10)

    # donut plot, split by %
    wedges, text = ax1.pie(list_pcent,
                           labels=text_c,
                           labeldistance=1.05,
                           colors=list_color,
                           textprops={'fontsize': 150, 'color': 'black'})
    #setup hole
    plt.setp(wedges, width=0.3)

    # add image in the center of donut plot
    img = mpimg.imread(resize_name)
    imagebox = OffsetImage(img, zoom=1.5)
    ab = AnnotationBbox(imagebox, (0, 0))
    ax1.add_artist(ab)

    ax1.set_aspect("equal")
    fig.set_facecolor('white')
    plt.tight_layout()

    output = io.BytesIO()

    #save as image
    fig.savefig(output, format='png')
    #encode for html
    encoded = base64.b64encode(output.getvalue()).decode('utf8')

    return render_template('result.html', photo=encoded)


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001,debug=True)