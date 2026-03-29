import { getDataTestIdElement } from "../../helpers";
import { createUser, logUserOn } from "../../steps/users";

describe("When a user orders breakfast twice using different names", () => {
  const username = `CypressUser${Date.now()}`;
  it("it is successfully ordered", () => {
    cy.visit("/");
    createUser(username);
    logUserOn(username);
    getDataTestIdElement("breakfast-signup-button").click();
    getDataTestIdElement("breakfast-signup-item-select").click();
    getDataTestIdElement("breakfast-signup-item-option").first().click();
    getDataTestIdElement("breakfast-signup-register").click();
    getDataTestIdElement("breakfast-signup-button").click();
    getDataTestIdElement("breakfast-signup-first-name").click().type("abc");
    getDataTestIdElement("breakfast-signup-item-select").click();
    getDataTestIdElement("breakfast-signup-item-option").first().click();
    getDataTestIdElement("breakfast-signup-register").click();
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item")
      .filter(`:contains(Breakfast sign-up)`)
      .should("have.length", 2);
  });

  it("the second order appears in the breakfast list", () => {
    cy.visit("/admin/breakfast");
    getDataTestIdElement("meal-receiver")
      .filter(`:contains(${username.toUpperCase()}ABC TEST)`)
      .should("have.length", 1);
  });
});
