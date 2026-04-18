import { getDataTestIdElement } from "../../../helpers";
import { createDinnerOrderApi, generateReceiver } from "../../../steps/orders";
import { createGuestUserApi, generateUsername } from "../../../steps/users";

describe("When an admin user signs a guest up for late dinner with a full name that has already been added", () => {
  const username = generateUsername();
  const receiver = generateReceiver(username);

  it("then they will be shown an error message and the guest will not be added to the meals", () => {
    createGuestUserApi(username);
    createDinnerOrderApi(username, receiver);
    cy.visit("/admin/dinner");
    getDataTestIdElement("meal-row")
      .filter(`:contains(${receiver})`)
      .should("have.length", 1);
    getDataTestIdElement("late-signup-button").click();
    getDataTestIdElement("late-signup-user-select-button").click();
    getDataTestIdElement(`late-signup-user-select-button-${username}`).click();
    getDataTestIdElement(`late-signup-user-select-button-${username}`).should(
      "not.exist",
    );
    getDataTestIdElement("late-signup-user-to-pay").should(
      "have.text",
      username,
    );
    getDataTestIdElement("late-signup-item-select").click();
    getDataTestIdElement("late-signup-item-option")
      .first()
      .invoke("text")
      .as("dinnerOption");
    cy.waitUntil(() => {
      Cypress.$("[data-testid=late-signup-item-option]").first().click();
      return Cypress.$("[data-testid=late-signup-item-option]").length === 0;
    });
    getDataTestIdElement("late-signup-register-button").click();
    cy.contains(
      `A guest with this full name (${receiver}) is already signed up for dinner! Change the full name to sign this guest up. The full name is not case sensitive.`,
    );
  });
});
