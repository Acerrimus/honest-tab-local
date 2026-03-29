import { getDataTestIdElement } from "../../helpers";
import { orderDinner } from "../../steps/ordering";
import { createUser, logUserOn } from "../../steps/users";

describe("When a user orders dinner twice using different names", () => {
  const username = `CypressUser${Date.now()}`;
  it("it is successfully ordered", () => {
    cy.visit("/");
    createUser(username);
    logUserOn(username);
    orderDinner(username);
    getDataTestIdElement("dinner-signup-button").click();
    getDataTestIdElement("dinner-signup-first-name").click().type("abc");
    getDataTestIdElement("dinner-signup-register").click();
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item")
      .filter(`:contains(Dinner sign-up)`)
      .should("have.length", 2);
  });

  it("the second order appears in the dinner list", () => {
    cy.visit("/admin/dinner");
    getDataTestIdElement("meal-receiver")
      .filter(`:contains(${username.toUpperCase()}ABC TEST)`)
      .should("have.length", 1);
  });
});
