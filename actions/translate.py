"""translate.py"""
import threading, json


def translate_action(parameters: dict, player=None) -> str:
    text        = parameters.get("text", "")
    target_lang = parameters.get("target_lang", "Hindi")
    source_lang = parameters.get("source_lang", "auto")

    if not text:
        return "No text to translate."

    try:
        from deep_translator import GoogleTranslator
        lang_codes = {
            "hindi":"hi","english":"en","french":"fr","spanish":"es","german":"de",
            "japanese":"ja","chinese":"zh-CN","arabic":"ar","russian":"ru",
            "portuguese":"pt","italian":"it","korean":"ko","dutch":"nl",
            "turkish":"tr","polish":"pl","urdu":"ur","bengali":"bn","tamil":"ta",
        }
        tgt_code = lang_codes.get(target_lang.lower(), target_lang.lower()[:2])
        src_code = "auto" if source_lang == "auto" else lang_codes.get(source_lang.lower(), "auto")

        translated = GoogleTranslator(source=src_code, target=tgt_code).translate(text)

        if player and hasattr(player, "anim"):
            def _show():
                player.anim.show(
                    anim_type="comparison",
                    title=f"Translation → {target_lang}",
                    content=json.dumps({
                        "headers": ["Original", "Translated"],
                        "rows": [[text[:60], translated[:60]]],
                    }),
                    color="#bf5fff",
                    duration=10,
                )
            threading.Thread(target=_show, daemon=True).start()

        return f"Translation ({target_lang}):\n{translated}"

    except ImportError:
        return "deep-translator not installed. Run: pip install deep-translator"
    except Exception as e:
        return f"Translation error: {e}"
