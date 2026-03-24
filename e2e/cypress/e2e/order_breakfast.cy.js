import { getDataTestIdElement } from "../helpers";
import { createUser, logUserOn } from "../steps/users";

describe("When a user orders breakfast", () => {
  const username = `CypressUser${Date.now()}`;
  it("it is successfully ordered", () => {
    cy.visit("/");
    createUser(username);
    logUserOn(username);
    getDataTestIdElement("breakfast-signup-button").click();
    getDataTestIdElement("breakfast-signup-first-name").should(
      "have.value",
      username,
    );
    getDataTestIdElement("breakfast-signup-last-name").should(
      "have.value",
      "Test",
    );
    getDataTestIdElement("breakfast-signup-item-select").click();
    getDataTestIdElement("breakfast-signup-item-option").first().click();
    getDataTestIdElement("breakfast-signup-allergies").should(
      "have.value",
      "Nuts",
    );
    getDataTestIdElement("breakfast-signup-register").click();
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item").contains("Breakfast sign-up");
  });

  it("the order appears in the breakfast list", () => {
    cy.visit("/admin/breakfast");
    getDataTestIdElement("meal-receiver")
      .filter(`:contains(${username.toUpperCase()} TEST)`)
      .should("have.length", 1);
  });
});
