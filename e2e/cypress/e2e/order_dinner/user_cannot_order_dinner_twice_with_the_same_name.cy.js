import { getDataTestIdElement } from "../../helpers";
import { orderDinner } from "../../steps/orders";
import { createUserAPI, generateUsername, logUserOn } from "../../steps/users";

describe("When a user orders dinner twice with the same name", () => {
  it("they will be shown an error", () => {
    const username = generateUsername();
    createUserAPI(username);
    cy.visit("/");
    logUserOn(username);
    orderDinner(username);
    getDataTestIdElement("dinner-signup-button").click();
    getDataTestIdElement("dinner-signup-register").click();
    cy.contains(
      "please provide different name if you want to sign up another person",
    );
  });
});
