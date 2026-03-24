import { getDataTestIdElement } from "../helpers";
import { createUser, logUserOn } from "../steps/users";

describe("When ordering dinner", () => {
  const username = `CypressUser${Date.now()}`;

  it("is successfully ordered", () => {
    cy.visit("/");
    createUser(username);
    logUserOn(username);
    getDataTestIdElement("dinner-signup-button").click();
    getDataTestIdElement("dinner-signup-first-name").should(
      "have.value",
      username,
    );
    getDataTestIdElement("dinner-signup-last-name").should(
      "have.value",
      "Test",
    );
    getDataTestIdElement("dinner-signup-allergies").should(
      "have.value",
      "Nuts",
    );
    getDataTestIdElement("dinner-signup-register").click();
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item").contains("Dinner sign-up");
    cy.get(`[data-testid="ordered_item"]`).contains("Dinner sign-up");
  });

  it("the order appears in the dinner list", () => {
    cy.visit("/admin/dinner");
    getDataTestIdElement("meal-receiver")
      .filter(`:contains(${username.toUpperCase()} TEST)`)
      .should("have.length", 1);
  });

  it("a user cannot order dinner twice with the same name", () => {
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("dinner-signup-button").click();
    getDataTestIdElement("dinner-signup-register").click();
    cy.contains("please provide different name if you want to sign up another person")
  })
});
