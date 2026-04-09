import { getDataTestIdElement } from "../../helpers";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a user orders breakfast twice with the same name", () => {
  it("it will not be ordered", () => {
    const username = generateUsername();
    createGuestUserApi(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("breakfast-signup-button").click();
    getDataTestIdElement("breakfast-signup-item-select").click();
    getDataTestIdElement("breakfast-signup-item-option").first().click();
    getDataTestIdElement("breakfast-signup-register").click();
    getDataTestIdElement("breakfast-signup-button").click();
    getDataTestIdElement("breakfast-signup-item-select").click();
    getDataTestIdElement("breakfast-signup-item-option").first().click();
    getDataTestIdElement("breakfast-signup-register").click();
    cy.contains(
      "please provide different name if you want to sign up another person",
    );
  });
});
