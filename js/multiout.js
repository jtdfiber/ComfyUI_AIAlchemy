import { app } from "../../../scripts/app.js";

// AI Alchemy · Encrypt End (the bridge). Connect each output the sealed region should EXPOSE
// into this node. Its inputs are dynamic (one trailing empty slot, like the Encrypt node's
// input_anything) and a matching output appears for every connected input — so N connected
// outputs -> N bridge outputs -> N Decrypt outputs. Fully mirrors the input side onto outputs.
const PREFIX = "input_anything";
const isDyn = (name) => typeof name === "string" && name.startsWith(PREFIX);

app.registerExtension({
  name: "alchemycrypto.multiout",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "AlchemyCryptoEncryptEnd") return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
      if (!this.inputs || this.inputs.length === 0) this.addInput(PREFIX, "*");
      this.__aiaSync();
      return r;
    };

    // Keep exactly one trailing empty input; one output per CONNECTED input, positionally aligned.
    nodeType.prototype.__aiaSync = function () {
      if (!this.inputs) return;
      // 1) ensure a trailing empty dynamic input
      const last = this.inputs[this.inputs.length - 1];
      if (!last || (isDyn(last.name) && last.link != null)) this.addInput(PREFIX, "*");
      // 2) remove empty dynamic slots that aren't the trailing one
      for (let i = this.inputs.length - 2; i >= 0; i--) {
        const s = this.inputs[i];
        if (isDyn(s.name) && s.link == null) this.removeInput(i);
      }
      // 3) renumber inputs: input_anything, input_anything1, input_anything2, ...
      let k = 0;
      for (const s of this.inputs) if (isDyn(s.name)) { s.name = k === 0 ? PREFIX : PREFIX + k; k++; }
      // 4) outputs: exactly one per connected input, named out0..outN-1
      const want = this.inputs.filter((s) => isDyn(s.name) && s.link != null).length;
      this.outputs = this.outputs || [];
      while (this.outputs.length < want) this.addOutput("out" + this.outputs.length, "*");
      while (this.outputs.length > want) this.removeOutput(this.outputs.length - 1);
      for (let i = 0; i < this.outputs.length; i++) this.outputs[i].name = "out" + i;
      this.setDirtyCanvas && this.setDirtyCanvas(true, true);
    };

    const onConnectionsChange = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function (slotType, slotIndex, isConnected, link, ioSlot) {
      const r = onConnectionsChange ? onConnectionsChange.apply(this, arguments) : undefined;
      // React to INPUT changes only (LiteGraph: type 1 = input). Skip during graph deserialization.
      if (slotType === 1) {
        const stack = (new Error()).stack || "";
        if (!stack.includes("configure") && !stack.includes("loadGraphData")) {
          try { this.__aiaSync(); } catch (e) {}
        }
      }
      return r;
    };
  },
});
