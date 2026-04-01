import { getDataTestIdElement } from "../../helpers";
import { orderDinner } from "../../steps/ordering";
import { createUserAPI, generateUsername, logUserOn } from "../../steps/users";

describe("When a user orders dinner", () => {
  const username = generateUsername();
  it("it is successfully ordered", () => {
    createUserAPI(username);
    cy.visit("/");
    logUserOn(username);
    orderDinner(username);
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item").contains("Dinner sign-up");
  });

  it("the order appears in the dinner list", () => {
    cy.visit("/admin/dinner");
    getDataTestIdElement("meal-receiver")
      .filter(`:contains(${username.toUpperCase()} TEST)`)
      .should("have.length", 1);
  });
});
