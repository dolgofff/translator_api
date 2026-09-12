from http import HTTPStatus

from django.http import JsonResponse
from django.views import View
from googletrans import Translator
from googletrans.constants import LANGUAGES


class Translate(View):
    async def get(self, request):
        try:
            source_language = request.GET.get("sl")
            destination_language = request.GET["dl"]
            text = request.GET["text"]

            async with Translator(
                service_urls=["translate.googleapis.com"],
                raise_exception=True,
            ) as translator:
                if source_language:
                    result = await translator.translate(
                        text,
                        src=source_language,
                        dest=destination_language,
                    )
                else:
                    result = await translator.translate(
                        text,
                        dest=destination_language,
                    )

            return JsonResponse(
                {
                    "source-language": result.src,
                    "source-text": result.origin,
                    "destination-language": result.dest,
                    "destination-text": result.text,
                }
            )

        except KeyError:
            return JsonResponse(
                {
                    "details": "dl or text fields are missing."
                },
                status=HTTPStatus.BAD_REQUEST,
            )

        except Exception as e:
            return JsonResponse(
                {
                    "error-type": type(e).__name__,
                    "error": str(e),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )


class Languages(View):
    def get(self, request):
        return JsonResponse(LANGUAGES)
