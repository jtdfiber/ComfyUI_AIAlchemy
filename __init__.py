from functools import partial, wraps
import logging
import os
import shutil
from .utils import get_local_app_setting_path
from .trim_workflow import WorkflowTrimHandler
from .crypto_node import (
    AlchemyCryptoEncrypt,
    AlchemyCryptoRandomSeed,
    AlchemyCryptoEncryptEnd,
    AlchemyCryptoDecrypt,
)
# Legacy (pre-entitlement) nodes — creator-machine only; not shipped in the public repo.
try:
    from .crypto_node_old import AlchemyCryptoOutput, AlchemyCryptoImage
    _LEGACY = {"AlchemyCryptoOutput": AlchemyCryptoOutput, "AlchemyCryptoImage": AlchemyCryptoImage}
except ImportError:
    _LEGACY = {}

NODE_CLASS_MAPPINGS = {
    "AlchemyCryptoEncrypt": AlchemyCryptoEncrypt,
    "AlchemyCryptoRandomSeed": AlchemyCryptoRandomSeed,
    "AlchemyCryptoEncryptEnd": AlchemyCryptoEncryptEnd,
    "AlchemyCryptoDecrypt": AlchemyCryptoDecrypt,
    **_LEGACY,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "AlchemyCryptoEncrypt": "AI Alchemy · Encrypt",
    "AlchemyCryptoRandomSeed": "AI Alchemy · Random Seed",
    "AlchemyCryptoEncryptEnd": "AI Alchemy · Encrypt End",
    "AlchemyCryptoDecrypt": "AI Alchemy · Decrypt",
    **({"AlchemyCryptoOutput": "AI Alchemy · Output", "AlchemyCryptoImage": "AI Alchemy · Image"} if _LEGACY else {}),
}
WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAMES_MAPPINGS", "WEB_DIRECTORY"]
from server import PromptServer
import aiohttp

workspace_path = os.path.join(os.path.dirname(__file__))
dist_path = os.path.join(workspace_path, "static")
if os.path.exists(dist_path):
    PromptServer.instance.app.add_routes(
        [aiohttp.web.static("/alchemycrypto/static", dist_path)]
    )
from urllib.parse import unquote
from .auth_unit import AuthUnit
from .updown_workflow import UploadWorkflow, UserWorkflowSetting

handler_instance = WorkflowTrimHandler()
onprompt_callback = partial(handler_instance.onprompt_handler)
PromptServer.instance.add_on_prompt_handler(onprompt_callback)
routes = PromptServer.instance.routes


@routes.post("/alchemycrypto/auth_callback")
async def auth_callback(request):
    auth_query = await request.json()
    token = auth_query.get("token", "")
    client_key = auth_query.get("client_key", "")
    if token and client_key:
        token = unquote(token)
        client_key = unquote(client_key)
        AuthUnit().set_user_token(token, client_key)
    return aiohttp.web.json_response({"status": "success"}, status=200)


@routes.post("/alchemycrypto/keygen")
async def keygen(request):
    data = await request.json()
    template_id = data.get("template_id", "").strip()
    if not template_id or len(template_id) != 32:
        return aiohttp.web.json_response(
            {"error_msg": "template_id is required"}, status=500
        )
    expire_date = data.get("expire_date", "")
    use_days = data.get("use_days", "")
    user_token, error_msg, error_code = AuthUnit().get_user_token()
    if not user_token:
        logging.error(f"crypto cat keygen failed: {error_msg}")
        return aiohttp.web.json_response({"error_msg": error_msg}, status=200)
    user_workflow = UploadWorkflow(user_token)
    serial_numbers = user_workflow.generate_serial_number(
        template_id, expire_date, use_days, 1
    )
    if not serial_numbers:
        logging.error(f"crypto cat keygen failed: {error_msg}")
        return aiohttp.web.json_response({"error_msg": "request failed"}, status=200)
    serial_number = serial_numbers[0]
    return aiohttp.web.json_response({"serial_number": serial_number}, status=200)


@routes.get("/alchemycrypto/clear")
async def logout(request):
    AuthUnit().clear_user_token()
    local_app_setting_path = get_local_app_setting_path()
    shutil.rmtree(local_app_setting_path, ignore_errors=True)
    return aiohttp.web.json_response({"status": "success"}, status=200)


@routes.post("/alchemycrypto/login")
async def login(request):
    user_token, error_msg, error_code = AuthUnit().get_user_token()
    if user_token and len(user_token) > 10 and error_code == 0:
        return aiohttp.web.json_response({"error_msg": "already connected"}, status=200)
    else:
        AuthUnit().login_dialog()
        return aiohttp.web.json_response(
            {"status": "success", "error_msg": "connecting..."}, status=200
        )


@routes.post("/alchemycrypto/set_long_token")
async def set_long_token(request):
    data = await request.json()
    long_token = data.get("long_token", "")
    AuthUnit().set_long_token(long_token)
    return aiohttp.web.json_response({"status": "success"}, status=200)


@routes.post("/alchemycrypto/set_auto_overwrite")
async def set_auto_overwrite(request):
    data = await request.json()
    auto_overwrite = data.get("auto_overwrite")
    UserWorkflowSetting().set_auto_overwrite(auto_overwrite)
    return aiohttp.web.json_response({"status": "success"}, status=200)
