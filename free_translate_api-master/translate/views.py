from http import HTTPStatus

import httpx
from django.http import JsonResponse
from django.views import View


LIBRETRANSLATE_URL = "https://libretranslate-production-3ae0.up.railway.app"


class Translate(View):
    async def get(self, request):
        source_language = request.GET.get("sl", "auto")
        destination_language = request.GET.get("dl")
        text = request.GET.get("text")

        if destination_language is None or text is None:
            return JsonResponse(
                {
                    "details": "dl or text fields are missing."
                },
                status=HTTPStatus.BAD_REQUEST,
            )

        payload = {
            "q": text,
            "source": source_language,
            "target": destination_language,
            "format": "text",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                libre_response = await client.post(
                    f"{LIBRETRANSLATE_URL}/translate",
                    json=payload,
                )

            libre_response.raise_for_status()
            data = libre_response.json()

        except httpx.HTTPStatusError as e:
            return JsonResponse(
                {
                    "error": "LibreTranslate returned an HTTP error.",
                    "details": str(e),
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        except httpx.RequestError as e:
            return JsonResponse(
                {
                    "error": "Could not connect to LibreTranslate.",
                    "details": str(e),
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        except ValueError:
            return JsonResponse(
                {
                    "error": "LibreTranslate returned invalid JSON."
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        translated_text = data.get("translatedText")

        if not translated_text:
            return JsonResponse(
                {
                    "error": "LibreTranslate response does not contain translation."
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        detected_language = get_detected_language(
            data=data,
            requested_source_language=source_language,
        )

        response = {
            "source-language": detected_language,
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


def get_detected_language(data, requested_source_language):
    if requested_source_language != "auto":
        return requested_source_language

    detected_language = data.get("detectedLanguage")

    if isinstance(detected_language, dict):
        language = detected_language.get("language")

        if language:
            return language

    if isinstance(detected_language, str) and detected_language:
        return detected_language

    return "auto"


class Languages(View):
    async def get(self, request):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                libre_response = await client.get(
                    f"{LIBRETRANSLATE_URL}/languages"
                )

            libre_response.raise_for_status()
            data = libre_response.json()

        except httpx.HTTPStatusError as e:
            return JsonResponse(
                {
                    "error": "LibreTranslate returned an HTTP error.",
                    "details": str(e),
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        except httpx.RequestError as e:
            return JsonResponse(
                {
                    "error": "Could not connect to LibreTranslate.",
                    "details": str(e),
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        except ValueError:
            return JsonResponse(
                {
                    "error": "LibreTranslate returned invalid JSON."
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        languages = {}

        for language in data:
            code = language.get("code")
            name = language.get("name")

            if code and name:
                languages[code] = name.lower()

        return JsonResponse(languages)
