import json
import base64
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import numpy as np
import cv2
import torch

# Load YOLOv5 model
try:
    model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)
    print("YOLOv5 model loaded successfully")
except Exception as e:
    print(f"Error loading YOLOv5 model: {str(e)}")

# Define waste categories
waste_categories = {
    'recyclable': [
        'bottle', 'can', 'paper', 'cardboard', 'plastic', 'cup', 'glass bottle', 'tin', 
        'aluminum', 'foil', 'plastic bag', 'straw', 'food container', 'magazine', 
        'newspaper', 'catalog', 'jar', 'milk carton', 'juice carton', 'soda can', 
        'water bottle', 'metal', 'shampoo bottle', 'detergent bottle', 'wrapping paper', 
        'plastic utensils', 'egg carton', 'cardboard box', 'envelope', 'aluminum can', 
        'metal can', 'steel', 'tin can', 'takeout container', 'plastic lid', 'card'
    ],
    'ewaste': [
        'cell phone', 'laptop', 'remote', 'tablet', 'computer', 'keyboard', 'mouse', 
        'charger', 'headphones', 'earbuds', 'monitor', 'television', 'printer', 'scanner', 
        'fax machine', 'camera', 'smartwatch', 'game console', 'dvd player', 'blu-ray player', 
        'router', 'modem', 'hard drive', 'flash drive', 'memory card', 'cord', 'cable', 
        'microwave', 'oven', 'stereo', 'speakers', 'projector', 'calculator', 'battery', 'batteries'
    ],
    'organic': [
        'apple', 'banana', 'carrot', 'orange', 'broccoli', 'lettuce', 'cucumber', 'tomato', 
        'grape', 'strawberry', 'pear', 'pineapple', 'peach', 'plum', 'kiwi', 'cherry', 
        'watermelon', 'mango', 'spinach', 'onion', 'pepper', 'avocado', 'potato', 'sweet potato', 
        'corn', 'peas', 'beans', 'eggplant', 'beet', 'celery', 'mushroom', 'zucchini', 
        'garlic', 'lemon', 'lime', 'ginger', 'cabbage', 'pumpkin', 'squash', 'radish', 'coconut',
        'eggshell', 'egg', 'coffee grounds', 'tea leaves', 'bread', 'cereal', 'pasta', 'rice', 'oatmeal',
        'chicken bone', 'fish bone', 'meat scraps'
    ]
}


# Classify waste
def classify_waste(label):
    for category, items in waste_categories.items():
        if label.lower() in items:
            return category
    return None

# Handle base64 image and classify it
@csrf_exempt
def classify_image(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data['image'].split(",")[1]
            image = Image.open(BytesIO(base64.b64decode(image_data)))
            img_array = np.array(image)

            # YOLOv5 inference
            results = model(img_array)
            detected_objects = results.pandas().xyxy[0]

            waste_classification_counts = {'recyclable': 0, 'ewaste': 0, 'organic': 0}
            detected_categories = set()

            for _, obj in detected_objects.iterrows():
                label = obj['name']
                confidence = obj['confidence']
                if confidence > 0.2:
                    category = classify_waste(label)
                    if category:
                        waste_classification_counts[category] += 1
                        detected_categories.add(category)

            detected_categories = ', '.join([category.capitalize() for category in detected_categories])

            return JsonResponse({
                'status': 'success',
                'classifications': waste_classification_counts,
                'detected_categories': detected_categories
            }, status=200)

        except Exception as e:
            print(f"Error during classification: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)
