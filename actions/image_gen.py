"""image_gen.py — Generate AI images using Pollinations.ai (free, no key)"""
import os, time, threading, urllib.request, urllib.parse


def image_gen(parameters: dict, player=None) -> str:
    prompt = parameters.get("prompt", "")
    style  = parameters.get("style", "realistic")
    size   = parameters.get("size", "1024x1024")

    if not prompt:
        return "No prompt provided."

    style_prompts = {
        "realistic": ", photorealistic, 8k, detailed",
        "anime":     ", anime style, vibrant colors, studio ghibli",
        "art":       ", digital art, artstation, trending",
        "3d":        ", 3d render, octane render, cinematic",
        "sketch":    ", pencil sketch, hand drawn, detailed",
    }
    full_prompt = prompt + style_prompts.get(style, "")
    encoded     = urllib.parse.quote(full_prompt)

    # Size
    w, h = 1024, 1024
    if "x" in size:
        parts = size.split("x")
        try: w, h = int(parts[0]), int(parts[1])
        except: pass

    url = f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&nologo=true"

    try:
        ts   = time.strftime("%Y%m%d_%H%M%S")
        path = f"/tmp/rahul_img_{ts}.png"

        if player:
            player.write_log("SYS: Generating image…")

        urllib.request.urlretrieve(url, path)

        if os.path.exists(path):
            if player:
                player.show_image(path)
                if hasattr(player, "anim"):
                    def _show():
                        player.anim.show(
                            anim_type="image",
                            title=prompt[:50],
                            content="",
                            color="#ff6600",
                            duration=15,
                            image_path=path,
                        )
                    threading.Thread(target=_show, daemon=True).start()
            return f"Image generated: {path}"
        return "Image generation failed."

    except Exception as e:
        return f"Image gen error: {e}"
