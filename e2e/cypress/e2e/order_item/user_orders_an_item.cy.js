import { getDataTestIdElement } from "../../helpers";
import { createUserAPI, generateUsername, logUserOn } from "../../steps/users";

describe("When a user orders an item", () => {
  const username = generateUsername();
  it("it is successfully ordered", () => {
    createUserAPI(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("order_item_button")
      .filter(":contains(TEST ITEM (€1.00))")
      .click();
    getDataTestIdElement("item_quantity_input").should("have.value", 1);
    getDataTestIdElement("item_total").contains("Total: €1");
    getDataTestIdElement("item_register").click();
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item").contains("TEST ITEM");
  });
});
