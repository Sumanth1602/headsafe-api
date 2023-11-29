from flask import Flask, request, jsonify
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import base64

app = Flask(__name__)

@app.route("/")
def index():
    # Extract image URL from the query parameter
    image_url = request.args.get('image')
    if not image_url:
        return jsonify({"error": "No image URL provided"}), 400

    # API endpoint with parameters for Roboflow
    api_key = 'w5ylLw3XPgiozxS1f1FZ'
    roboflow_url = f"https://detect.roboflow.com/hard-hat-workers/13?api_key={api_key}&image={image_url}"

    # Send POST request to Roboflow API
    roboflow_response = requests.post(roboflow_url)
    predictions = roboflow_response.json()

    # Fetch and load the image
    image_response = requests.get(image_url)
    image = Image.open(BytesIO(image_response.content))

    # Drawing the boxes
    draw = ImageDraw.Draw(image)
    for prediction in predictions['predictions']:
        # Calculate the rectangle coordinates
        top_left_x = prediction['x'] - prediction['width'] / 2
        top_left_y = prediction['y'] - prediction['height'] / 2
        bottom_right_x = prediction['x'] + prediction['width'] / 2
        bottom_right_y = prediction['y'] + prediction['height'] / 2
        
        # Draw the rectangle on the image
        draw.rectangle(((top_left_x, top_left_y), (bottom_right_x, bottom_right_y)), 
                       outline="green", width=20)

    # Save the modified image to a bytes buffer
    buf = BytesIO()
    image.save(buf, format='JPEG', quality=25)
    buf.seek(0)

    # Encode the modified image to base64
    encoded_image = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Prepare data for the POST request to the image hosting service
    data = {
        "key": "6d207e02198a847aa98d0a2a901485a5",
        "source": encoded_image,
        "action": "upload"
    }

    # Send POST request to freeimage.host
    upload_response = requests.post("https://freeimage.host/api/1/upload", data=data).json()

    # Check the response and append the URL
    if 'status_code' in upload_response and upload_response['status_code'] == 200:
        predictions['image_url'] = upload_response['image']['url']
    else:
        predictions['image_url'] = "Error in image upload"

    # Return the JSON response
    return jsonify(predictions)

if __name__ == "__main__":
    app.run()
