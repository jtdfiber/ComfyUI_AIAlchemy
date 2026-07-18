import json
import os
import random
import uuid
import torch
from comfy_execution.graph import ExecutionBlocker
from comfy_execution.graph_utils import GraphBuilder
from .updown_workflow import UploadWorkflow
from server import PromptServer
from .trim_workflow import AlchemyWorkflow, AlchemyDecodeWorkflow
from .auth_unit import AuthUnit


class AlchemyCryptoEncrypt:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"template_id": ("STRING", {"default": uuid.uuid4().hex})},
            "optional": {"input_anything": ("*", {})},
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "crypto"
    CATEGORY = "AI Alchemy"

    @classmethod
    def IS_CHANGED(s, **kwargs):
        return float("NaN")

    @classmethod
    def VALIDATE_INPUTS(s, input_types):
        return True

    def crypto(self, template_id, **kwargs):
        unique_id = kwargs.pop("unique_id", None)
        prompt = kwargs.pop("prompt", None)
        extra_pnginfo = kwargs.pop("extra_pnginfo", None)
        if unique_id is None:
            raise Exception("Warning: 'unique_id' is missing.")
        if prompt is None:
            raise Exception("Warning: 'prompt' is missing.")
        template_id = (template_id or "").strip()
        if len(template_id) < 2:
            raise Exception("Give this rig a workflow id (e.g. vton_v1).")
        crypto_workflow = AlchemyWorkflow(extra_pnginfo["workflow"], prompt, template_id)
        crypto_workflow.invalid_workflow()
        crypto_workflow.load_workflow()
        crypto_workflow.load_prompt()
        crypto_workflow.analysis_node()
        crypto_dir = crypto_workflow.calculate_crypto_result(
            f"crypto_{template_id}.json"
        )
        output_dir = crypto_workflow.output_workflow_simple_shell(
            f"alchemycrypto_{template_id}.json"
        )
        crypto_workflow.save_original_workflow(
            f"original_workflow_{template_id}.json", crypto_dir
        )
        crypto_workflow.save_original_prompt(
            f"original_prompt_{template_id}.json", crypto_dir
        )
        user_token, error_msg, error_code = AuthUnit().get_user_token()
        if not user_token:
            print(f"AI Alchemy upload failed: {error_msg}")
            PromptServer.instance.send_sync(
                "alchemycrypto_toast",
                {"content": f"AI Alchemy: no creator token — set it in server.json ({error_msg})", "type": "error"},
            )
            return (ExecutionBlocker(None),)
        upload = UploadWorkflow(user_token)
        ret = upload.upload_workflow(template_id, crypto_dir)
        if not ret:
            print("AI Alchemy upload failed")
            return (ExecutionBlocker(None),)
        # Entitlement model: no serials minted here. The blob is now escrowed under
        # this id; grant buyers access (Stripe or the console) and they get their key.
        PromptServer.instance.send_sync(
            "alchemycrypto_toast",
            {"content": f"AI Alchemy: '{template_id}' encrypted + uploaded. Add its files + link a product in the console.",
             "type": "info", "duration": 6000},
        )
        return (template_id,)


class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


any = AnyType("*")


class AlchemyCryptoEncryptEnd:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"value": (any,)}}

    @classmethod
    def VALIDATE_INPUTS(s, input_types):
        return True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    RETURN_TYPES = (any,)
    FUNCTION = "doit"
    CATEGORY = "AI Alchemy"

    def doit(self, value):
        return (value,)


def is_link(obj):
    if not isinstance(obj, list):
        return False
    if len(obj) != 2:
        return False
    if not isinstance(obj[0], str):
        return False
    if (
        not isinstance(obj[1], int)
        and not isinstance(obj[1], float)
        and not isinstance(obj[1], str)
    ):
        return False
    return True


class AlwaysEqualProxy(str):
    def __eq__(self, _):
        return True

    def __ne__(self, _):
        return False


class AlwaysTupleZero(tuple):
    def __getitem__(self, _):
        return AlwaysEqualProxy(super().__getitem__(0))


class AlchemyCryptoDecrypt:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "template_id": ("STRING",),
                "serial_number": (
                    "STRING",
                    {"multiline": True, "placeholder": "Paste your AI Alchemy license key"},
                ),
            },
            "optional": {"input_anything": (any,)},
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    @classmethod
    def VALIDATE_INPUTS(s, input_types):
        return True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    RETURN_TYPES = AlwaysTupleZero(AlwaysEqualProxy("*"))
    FUNCTION = "decode"
    CATEGORY = "AI Alchemy"
    OUTPUT_NODE = False

    def decode(self, template_id, serial_number, **kwargs):
        unique_id = kwargs.pop("unique_id", None)
        prompt = kwargs.pop("prompt", None)
        extra_pnginfo = kwargs.pop("extra_pnginfo", None)
        decode_crypto_workflow = AlchemyDecodeWorkflow(
            prompt, extra_pnginfo["workflow"], template_id
        )
        crypto_prompt = decode_crypto_workflow.load_crypto_prompt(serial_number)
        decode_crypto_workflow.calculate_input_anything_map()
        processed_nodes = {}
        graph = GraphBuilder()

        def get_node_result(nodeData, id):
            inputKeys = []
            for ikey in nodeData["inputs"].keys():
                input_value = nodeData["inputs"][ikey]
                if (
                    is_link(input_value)
                    and decode_crypto_workflow.get_hidden_input(input_value) is None
                    and input_value[0] not in processed_nodes
                ):
                    inputKeys.append(input_value[0])
            for ikey in inputKeys:
                if ikey not in crypto_prompt:
                    continue
                node = get_node_result(crypto_prompt[ikey], ikey)
                processed_nodes[ikey] = node
            inputs = nodeData["inputs"]
            newInputs = {}
            for ikey in inputs.keys():
                if is_link(inputs[ikey]):
                    hidden_input_name = decode_crypto_workflow.get_hidden_input(
                        inputs[ikey]
                    )
                    if hidden_input_name:
                        if hidden_input_name in kwargs:
                            newInputs[ikey] = kwargs[hidden_input_name]
                    elif inputs[ikey][0] in processed_nodes:
                        newInputs[ikey] = processed_nodes[inputs[ikey][0]].out(
                            inputs[ikey][1]
                        )
                else:
                    newInputs[ikey] = inputs[ikey]
            return graph.node(nodeData["class_type"], id, **newInputs)

        node_id, link_idx = decode_crypto_workflow.get_outputs()
        nodeData = crypto_prompt[node_id]
        node = get_node_result(nodeData, node_id)
        value = node.out(link_idx)
        return {"result": tuple([value]), "expand": graph.finalize()}


class AlchemyCryptoRandomSeed:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}, "optional": {}, "hidden": {}}

    RETURN_TYPES = ("INT",)
    FUNCTION = "random"
    CATEGORY = "AI Alchemy"

    def IS_CHANGED():
        return float("NaN")

    def random(self):
        return (random.randint(0, 999999),)
