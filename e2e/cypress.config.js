const { defineConfig } = require("cypress");

module.exports = defineConfig({
  video: true,
  defaultCommandTimeout: 20000,
  e2e: {
    baseUrl: "http://app:3000",
  },
});
