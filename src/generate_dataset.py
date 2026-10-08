"""Generate the waste image dataset with FLUX.1 Schnell through a ComfyUI server.

Each class has five text prompts. For every image, one prompt is picked at random and
combined with a photorealistic style prompt, then sent to ComfyUI's API.

Based on the ComfyUI example from the course. Needs a running ComfyUI instance and the
FLUX.1 Schnell text-to-image workflow exported in API format (workflow_flux_api.json).
Connection details are read from environment variables; see .env.example.

Usage:
    python src/generate_dataset.py --images-per-class 100 --out data/dataset
"""
import argparse
import base64
import io
import json
import os
import random
import urllib.parse
import urllib.request
import uuid

import websocket  # pip install websocket-client

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

COMFYUI_SERVER = os.environ["COMFYUI_SERVER"]  # host[:port], without http://
COMFYUI_WORKFLOW = os.environ.get("COMFYUI_WORKFLOW", "workflow_flux_api.json")
_credentials = base64.b64encode(
    f"{os.environ['COMFYUI_USERNAME']}:{os.environ['COMFYUI_PASSWORD']}".encode("utf-8")
).decode("utf-8")
AUTH_HEADER = {"Authorization": f"Basic {_credentials}"}
CLIENT_ID = str(uuid.uuid4())

CLASS_PROMPTS = {
    "PMD": [
        "A mix of plastic bottles, aluminum cans, and juice cartons scattered across a wooden table.",
        "A pile of empty plastic packaging, crushed soda cans, and a milk carton on a rough stone surface.",
        "Assorted plastic containers, metal cans, and foil wrappers spread out on a kitchen countertop.",
        "Plastic food trays, a disposable plastic cup with a straw, and a dented aluminum can left on a bench.",
        "A flattened plastic water bottle, an empty metal soup can, and a slightly crumpled juice box placed together.",
    ],
    "Paper & Cardboard": [
        "A bundle of old newspapers, flattened cardboard boxes, and torn notebook pages stacked on a table.",
        "Loose sheets of printed paper, discarded magazines, and a few small cardboard packages on the floor.",
        "A pile of used paper bags, opened envelopes, and crumpled pages from a notebook.",
        "A collection of worn-out books, newspapers, and a torn cereal box left on the sidewalk.",
        "Scattered shredded paper, junk mail envelopes, and broken-down shipping boxes on a desk.",
    ],
    "Organic Waste": [
        "A mixture of vegetable peels, fruit rinds, and eggshells placed on a wooden tray.",
        "Banana peels, used coffee grounds, and damp tea bags collected in a compost bin.",
        "A heap of food leftovers, including pizza crusts, pasta remnants, and vegetable scraps on a plate.",
        "Rotten tomatoes, wilted spinach leaves, and carrot tops discarded in a compost heap.",
        "A close-up of apple cores, orange peels, and potato skins arranged on a kitchen cutting board.",
    ],
    "General Waste": [
        "A pile of mixed trash, including greasy napkins, plastic utensils, and a torn candy wrapper.",
        "A collection of broken objects such as a snapped pencil, torn fabric scraps, and a used sponge.",
        "Crumpled tissues, an old disposable razor, and a dried-out marker lying in a trash bin.",
        "Scattered snack wrappers, used plastic straws, and a crushed disposable coffee cup.",
        "A pile of non-recyclable waste, including a cracked phone case, foil-lined wrappers, and rubber bands.",
    ],
}

# Added to every prompt so only realistic images are generated
STYLE_PROMPT = "Photography, highly detailed, sharp focus, hyperrealism."


def comfyui_queue_prompt(prompt):
    data = json.dumps({"prompt": prompt, "client_id": CLIENT_ID}).encode("utf-8")
    req = urllib.request.Request(f"http://{COMFYUI_SERVER}/prompt", data=data, headers=AUTH_HEADER)
    return json.loads(urllib.request.urlopen(req).read())


def comfyui_get_image(filename, subfolder, folder_type):
    query = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
    req = urllib.request.Request(f"http://{COMFYUI_SERVER}/view?{query}", headers=AUTH_HEADER)
    with urllib.request.urlopen(req) as response:
        return response.read()


def comfyui_get_history(prompt_id):
    req = urllib.request.Request(f"http://{COMFYUI_SERVER}/history/{prompt_id}", headers=AUTH_HEADER)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())


def comfyui_get_images(ws, prompt):
    """Queue a workflow, wait until it finishes, and return the generated images per node."""
    prompt_id = comfyui_queue_prompt(prompt)["prompt_id"]
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                data = message["data"]
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break

    history = comfyui_get_history(prompt_id)[prompt_id]
    output_images = {}
    for node_id, node_output in history["outputs"].items():
        if "images" in node_output:
            output_images[node_id] = [
                comfyui_get_image(img["filename"], img["subfolder"], img["type"])
                for img in node_output["images"]
            ]
    return output_images


def comfyui_generate_image_flux(prompt, seed, output_filename):
    with open(COMFYUI_WORKFLOW, "r") as file:
        workflow = json.load(file)

    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    # Node ids depend on the workflow (see workflow_flux_api.json)
    workflow["6"]["inputs"]["text"] = prompt
    workflow["25"]["inputs"]["noise_seed"] = seed

    ws = websocket.WebSocket()
    ws.connect(f"ws://{COMFYUI_SERVER}/ws?clientId={CLIENT_ID}", header=AUTH_HEADER)
    images = comfyui_get_images(ws, workflow)

    if images:
        with open(output_filename, "wb") as outfile:
            outfile.write(io.BytesIO(images["9"][0]).getbuffer())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--images-per-class", type=int, default=100)
    parser.add_argument("--out", default=os.path.join("data", "dataset"))
    args = parser.parse_args()

    for category, prompts in CLASS_PROMPTS.items():
        class_dir = os.path.join(args.out, category)
        os.makedirs(class_dir, exist_ok=True)
        for i in range(args.images_per_class):
            prompt = random.choice(prompts)
            image_path = os.path.join(class_dir, f"{category}_{i + 1}.png")
            comfyui_generate_image_flux(f"{prompt} {STYLE_PROMPT}", -1, image_path)
            print(f"Generated image: {image_path}")


if __name__ == "__main__":
    main()
