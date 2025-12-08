import { baseService } from "./service.js";
const noopService = {
  ...baseService,
  propertiesToHash: ["src"],
  async validateOptions(options, imageConfig) {
    const newOptions = await (baseService.validateOptions?.(options, imageConfig) ?? options);
    delete newOptions.format;
    return newOptions;
  },
  async transform(inputBuffer, transformOptions) {
    return {
      data: inputBuffer,
      format: transformOptions.format
    };
  }
};
var noop_default = noopService;
export {
  noop_default as default
};
