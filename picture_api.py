from flask import request
import replicate
import os

# Get the API token from the .env file
api_token = os.getenv('REPLICATE_API_TOKEN')



# Define the parameters to the API
model_prompt = ""
num_samples = "1"
image_resolution = "512"
ddim_steps = 20
scale = 9
seed = None
eta = 0
a_prompt = "best quality"
n_prompt = "longbody, toys, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality"
detect_resolution = 512
value_threshold = 0.1
distance_threshold = 0.1


# function takes in the image path and returns the output from the API
def replicate_api_function(room_input, style_input, image_path):
    model_prompt = f"Remodel this {room_input} and make it look like a {style_input} style."
    output = replicate.run(
        "jagilley/controlnet-hough:854e8727697a057c525cdb45ab037f64ecca770a1769cc52287c2e56472a247b",
    #   input={"image": open(os.path.join(image_path, uploaded_filename), "rb"), "prompt": model_prompt},
        input={"image": open(image_path, "rb"), "prompt": model_prompt},
        params={
            "num_samples": num_samples,
            "image_resolution": image_resolution,
            "ddim_steps": ddim_steps,
            "scale": scale,
            "seed": seed,
            "eta": eta,
            "a_prompt": a_prompt,
            "n_prompt": n_prompt,
            "detect_resolution": detect_resolution,
            "value_threshold": value_threshold,
            "distance_threshold": distance_threshold
        }
    )

    print('SUCCESSFULLY CALLED REPLICATE API')
    print("MODEL PROMPT:", f"'{model_prompt}'")
    return output
