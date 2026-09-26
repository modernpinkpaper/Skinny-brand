"""Makes 1 test image with one free image model, on a normal computer (no graphics card), and times it.

  python try_model.py <model key> <out folder>

Models (all run through the free `diffusers` library):
  dreamshaper       Dreamshaper 8 (Stable Diffusion 1.5 family), 25 steps  - free for commercial use
  dreamshaper-lcm   the same + LCM speed-up, 6 steps                        - free for commercial use
  sdxl              Stable Diffusion XL 1.0, 25 steps                       - free for commercial use
  sdxl-lcm          SDXL + LCM speed-up, 6 steps                            - free for commercial use
  sdxl-turbo        SDXL Turbo, 2 steps (fastest; NOT free for commercial use - speed reference only)"""
import os, sys, json, time, resource
import torch
from diffusers import AutoPipelineForText2Image, LCMScheduler

PROMPT = ("soft painterly animated illustration, a young woman quietly packing a suitcase at night in a dim apartment, "
          "warm lamp light, rain on the window, moody muted colors, cinematic, detailed, no text")
NEGATIVE = "text, letters, watermark, logo, blurry, deformed hands, extra fingers, ugly"
MODELS = {
    "dreamshaper":     dict(repo="Lykon/dreamshaper-8", steps=25, guidance=7.0, size=(768, 576), license="CreativeML OpenRAIL-M (commercial use allowed)"),
    "dreamshaper-lcm": dict(repo="Lykon/dreamshaper-8", lora="latent-consistency/lcm-lora-sdv1-5", steps=6, guidance=1.5, size=(768, 576), license="CreativeML OpenRAIL-M (commercial use allowed)"),
    "sdxl":            dict(repo="stabilityai/stable-diffusion-xl-base-1.0", steps=25, guidance=7.0, size=(1024, 768), license="CreativeML OpenRAIL++-M (commercial use allowed)"),
    "sdxl-lcm":        dict(repo="stabilityai/stable-diffusion-xl-base-1.0", lora="latent-consistency/lcm-lora-sdxl", steps=6, guidance=1.5, size=(1024, 768), license="CreativeML OpenRAIL++-M (commercial use allowed)"),
    "sdxl-turbo":      dict(repo="stabilityai/sdxl-turbo", steps=2, guidance=0.0, size=(768, 576), license="Stability AI non-commercial research license (NOT for monetized videos)"),
}

key, out = sys.argv[1], sys.argv[2]
m = MODELS[key]; os.makedirs(out, exist_ok=True)
torch.set_num_threads(os.cpu_count())
t0 = time.time()
# SDXL is big: load the half-size download and run it in bfloat16 so it fits a 16 GB computer
dtype = torch.bfloat16 if "xl" in m["repo"] else torch.float32
try: pipe = AutoPipelineForText2Image.from_pretrained(m["repo"], torch_dtype=dtype, variant="fp16")
except (OSError, ValueError): pipe = AutoPipelineForText2Image.from_pretrained(m["repo"], torch_dtype=dtype)
if m.get("lora"):
    pipe.load_lora_weights(m["lora"]); pipe.fuse_lora(); pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
load = time.time() - t0
w, h = m["size"]
t1 = time.time()
img = pipe(PROMPT, negative_prompt=NEGATIVE if m["guidance"] > 1 else None, num_inference_steps=m["steps"],
           guidance_scale=m["guidance"], width=w, height=h, generator=torch.Generator().manual_seed(7)).images[0]
gen = time.time() - t1
img.save(os.path.join(out, f"{key}.png"))
res = dict(model=key, repo=m["repo"], steps=m["steps"], size=f"{w}x{h}", download_and_load_seconds=round(load),
           image_seconds=round(gen), license=m["license"], cpus=os.cpu_count(),
           memory_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024, 1))
json.dump(res, open(os.path.join(out, f"{key}.json"), "w"))
print(json.dumps(res, indent=1))
