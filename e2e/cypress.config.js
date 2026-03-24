const { defineConfig } = require("cypress");

module.exports = defineConfig({
  defaultCommandTimeout: 20000,
  e2e: {
    baseUrl: "http://app:3000",
  },
});
