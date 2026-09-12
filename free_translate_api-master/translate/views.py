import os
from http import HTTPStatus
from urllib.parse import quote

import httpx
from django.http import JsonResponse
from django.views import View


LINGVA_BASE_URL = os.getenv(
    "LINGVA_BASE_URL",
    "https://translate.jae.fi",
).rstrip("/")


class Translate(View):
    async def get(self, request):
        source_language = request.GET.get("sl", "auto")
        destination_language = request.GET.get("dl")
        text = request.GET.get("text")

        if destination_language is None or text is None:
            return JsonResponse(
                {"details": "dl or text fields are missing."},
                status=HTTPStatus.BAD_REQUEST,
            )

        encoded_text = quote(text, safe="")

        url = (
            f"{LINGVA_BASE_URL}/api/v1/"
            f"{source_language}/"
            f"{destination_language}/"
            f"{encoded_text}"
        )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                lingva_response = await client.get(url)

            lingva_response.raise_for_status()
            data = lingva_response.json()

        except httpx.HTTPStatusError as e:
            return JsonResponse(
                {
                    "error": "Lingva returned an HTTP error.",
                    "details": str(e),
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        except httpx.RequestError as e:
            return JsonResponse(
                {
                    "error": "Could not connect to Lingva.",
                    "details": str(e),
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        except ValueError:
            return JsonResponse(
                {
                    "error": "Lingva returned invalid JSON.",
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        if "error" in data:
            return JsonResponse(
                {
                    "error": data["error"],
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        translated_text = data.get("translation")

        if translated_text is None:
            return JsonResponse(
                {
                    "error": "Lingva response does not contain translation.",
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

    info = data.get("info")

    if not isinstance(info, dict):
        return "auto"

    detected = info.get("detected")

    if isinstance(detected, dict):
        code = detected.get("code")

        if code:
            return code

    detected_source = info.get("detectedSource")

    if isinstance(detected_source, str) and detected_source:
        return detected_source

    return "auto"


class Languages(View):
    async def get(self, request):
        url = f"{LINGVA_BASE_URL}/api/v1/languages"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                lingva_response = await client.get(url)

            lingva_response.raise_for_status()
            data = lingva_response.json()

        except (httpx.HTTPError, ValueError) as e:
            return JsonResponse(
                {
                    "error": "Could not load languages from Lingva.",
                    "details": str(e),
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        languages = data.get("languages")

        if not isinstance(languages, list):
            return JsonResponse(
                {
                    "error": "Lingva returned invalid languages response.",
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

        # Сохраняем старый контракт googletrans:
        # {
        #     "en": "english",
        #     "ru": "russian",
        #     ...
        # }
        response = {
            language["code"]: language["name"].lower()
            for language in languages
            if "code" in language and "name" in language
        }

        return JsonResponse(response)
