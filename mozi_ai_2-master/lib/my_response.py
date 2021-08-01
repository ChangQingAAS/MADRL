from rest_framework.response import Response


class MyResponse(Response):
    def __init__(self, code=200, msg="Success", data="", status=None,
                 template_name=None, headers=None,
                 exception=False, content_type=None):
        super(MyResponse, self).__init__(data, status, template_name, headers,
                                         exception, content_type)

        self.data = {"code": code, "msg": msg, "data": data}
