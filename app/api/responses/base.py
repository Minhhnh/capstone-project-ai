from fastapi.responses import JSONResponse
from starlette import status


class BaseResponse:
    def __init__(self) -> None:
        self.base_response = {
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "",
            "data": None,
        }

    @staticmethod
    def success_response(message="API success", status_code=status.HTTP_200_OK):
        """
        This is a Python function that returns a JSON response with a default success message and status
        code.
        
        :param message: The message parameter is a string that represents the success message that will be
        returned in the API response. If no message is provided, the default message "API success" will be
        used, defaults to API success (optional)
        :param status_code: The HTTP status code to be returned in the response. It defaults to 200 (OK) if
        not specified
        :return: a JSONResponse object with a default message of "API success" and a default status code of
        200. The content of the response includes a "status" key with a value of "failed", a "status_code"
        key with the provided status code, and a "message" key with the provided message.
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "failed",
                "status_code": status_code,
                "message": message,
            })

    @staticmethod
    def error_response(message="API error", status_code=status.HTTP_400_BAD_REQUEST):
        """
        This is a Python function that returns a JSON response with an error message and status code.
        
        :param message: The error message to be returned in the response. The default value is "API error"
        if no message is provided when the function is called, defaults to API error (optional)
        :param status_code: The HTTP status code to be returned in the response. It is set to a default
        value of 400 (Bad Request) if not specified
        :return: The function `error_response` is returning a JSON response with a status code, a status
        message, and a custom message. The default status code is `status.HTTP_400_BAD_REQUEST` and the
        default message is "API error".
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "failed",
                "status_code": status_code,
                "message": message,
            })


response = BaseResponse()
