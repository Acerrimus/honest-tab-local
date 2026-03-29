import { getDataTestIdElement } from "../../helpers";
import { createUser, logUserOn } from "../../steps/users";

describe("When a user orders breakfast twice with the same name", () => {
  const username = `CypressUser${Date.now()}`;
  it("it will not be ordered", () => {
    cy.visit("/");
    createUser(username);
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
