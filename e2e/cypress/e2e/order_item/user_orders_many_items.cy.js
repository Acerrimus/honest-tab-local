import { getDataTestIdElement } from "../../helpers";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a user orders many items", () => {
  const username = generateUsername();
  it("they are all successfully ordered", () => {
    createGuestUserApi(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("order_item_button")
      .filter(":contains(TEST ITEM (€1.00))")
      .click();
    getDataTestIdElement("item_quantity_input").click().type(5);
    getDataTestIdElement("item_total").contains("Total: €5");
    getDataTestIdElement("item_register").click();
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item").contains("TEST ITEM");
    getDataTestIdElement("ordered_item_quantity").contains(5);
    getDataTestIdElement("ordered_item_total").contains("€5.00");
  });
});
