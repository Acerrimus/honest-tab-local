import { getDataTestIdElement } from "../helpers";

export function createUser(username) {
  getDataTestIdElement("sign-up-user-button").click();
  getDataTestIdElement("user-name-input").click().type(username);
  getDataTestIdElement("first-name-input").click().type("Cypress");
  getDataTestIdElement("last-name-input").click().type("Test");
  getDataTestIdElement("phone-number-input").click().type("0123456789");
  getDataTestIdElement("email-input").click().type("test@test.com");
  cy.get('select[name="diet"]').select("Vegan", { force: true });
  getDataTestIdElement("allergies-input").click().type("Nuts");
  getDataTestIdElement("radio-input-yes").click();
  getDataTestIdElement("user-submit-button").click();
}

export function logUserOn(username, password = "test@") {
  cy.get(`[data-testid="user-button-${username}"]`, { timeout: 10000 }).click();
  getDataTestIdElement("user-email-password").click().type(password);
  getDataTestIdElement("password-submit-button").click();
}
