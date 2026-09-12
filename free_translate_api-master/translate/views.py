from http import HTTPStatus

import httpx
from django.http import JsonResponse
from django.views import View
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


MYMEMORY_URL = "https://api.mymemory.translated.net/get"


class Translate(View):
    async def get(self, request):
        source_language = request.GET.get("sl")
        destination_language = request.GET.get("dl")
        text = request.GET.get("text")

        if destination_language is None or text is None:
            return JsonResponse(
                {"details": "dl or text fields are missing."},
                status=HTTPStatus.BAD_REQUEST,
            )

        if len(text.encode("utf-8")) > 500:
            return JsonResponse(
                {
                    "details": "Text is too long. MyMemory accepts a maximum of 500 bytes."
                },
                status=HTTPStatus.BAD_REQUEST,
            )

        if source_language is None:
            try:
                source_language = detect(text)
                source_language = normalize_language_code(source_language)
            except LangDetectException:
                return JsonResponse(
                    {
                        "details": "Could not detect source language."
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )

        params = {
            "q": text,
            "langpair": f"{source_language}|{destination_language}",
            "mt": "1",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                mymemory_response = await client.get(
                    MYMEMORY_URL,
                    params=params,
                )

            mymemory_response.raise_for_status()
            data = mymemory_response.json()

        except httpx.HTTPStatusError as e:
            return JsonResponse(
                {
                    "error": "MyMemory returned an HTTP error.",
                    "details": str(e),
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        except httpx.RequestError as e:
            return JsonResponse(
                {
                    "error": "Could not connect to MyMemory.",
                    "details": str(e),
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        except ValueError:
            return JsonResponse(
                {
                    "error": "MyMemory returned invalid JSON.",
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        response_data = data.get("responseData")

        if not isinstance(response_data, dict):
            return JsonResponse(
                {
                    "error": "MyMemory response does not contain responseData."
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        translated_text = response_data.get("translatedText")

        if not translated_text:
            return JsonResponse(
                {
                    "error": "MyMemory response does not contain translation."
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        response = {
            "source-language": source_language,
            "source-text": text,
            "destination-language": destination_language,
            "destination-text": translated_text,
            "pronunciation": {
                "source-text-phonetic": None,
                "source-text-audio": None,
                "destination-text-audio": None,
            },
            "translations": {
                "all-translations": None,
                "possible-translations": None,
                "possible-mistakes": None,
            },
            "definitions": None,
            "see-also": None,
        }

        return JsonResponse(response)


def normalize_language_code(code):
    mapping = {
        "zh-cn": "zh-CN",
        "zh-tw": "zh-TW",
    }

    return mapping.get(code, code)


class Languages(View):
    def get(self, request):
        languages = {
            "af": "afrikaans",
            "sq": "albanian",
            "ar": "arabic",
            "az": "azerbaijani",
            "eu": "basque",
            "bn": "bengali",
            "be": "belarusian",
            "bg": "bulgarian",
            "ca": "catalan",
            "zh-CN": "chinese simplified",
            "zh-TW": "chinese traditional",
            "hr": "croatian",
            "cs": "czech",
            "da": "danish",
            "nl": "dutch",
            "en": "english",
            "eo": "esperanto",
            "et": "estonian",
            "tl": "filipino",
            "fi": "finnish",
            "fr": "french",
            "gl": "galician",
            "ka": "georgian",
            "de": "german",
            "el": "greek",
            "gu": "gujarati",
            "ht": "haitian creole",
            "he": "hebrew",
            "hi": "hindi",
            "hu": "hungarian",
            "is": "icelandic",
            "id": "indonesian",
            "ga": "irish",
            "it": "italian",
            "ja": "japanese",
            "kn": "kannada",
            "ko": "korean",
            "la": "latin",
            "lv": "latvian",
            "lt": "lithuanian",
            "mk": "macedonian",
            "ms": "malay",
            "mt": "maltese",
            "no": "norwegian",
            "fa": "persian",
            "pl": "polish",
            "pt": "portuguese",
            "ro": "romanian",
            "ru": "russian",
            "sr": "serbian",
            "sk": "slovak",
            "sl": "slovenian",
            "es": "spanish",
            "sw": "swahili",
            "sv": "swedish",
            "ta": "tamil",
            "te": "telugu",
            "th": "thai",
            "tr": "turkish",
            "uk": "ukrainian",
            "ur": "urdu",
            "vi": "vietnamese",
            "cy": "welsh",
        }

        return JsonResponse(languages)
