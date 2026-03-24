import { getDataTestIdElement } from "../../helpers";
import { orderDinner } from "../../steps/ordering";
import { createUser, logUserOn } from "../../steps/users";

describe("When a user orders dinner", () => {
  const username = `CypressUser${Date.now()}`;
  it("it is successfully ordered", () => {
    cy.visit("/");
    createUser(username);
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
