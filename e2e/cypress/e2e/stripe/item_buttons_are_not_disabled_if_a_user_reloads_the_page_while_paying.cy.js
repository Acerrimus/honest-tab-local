import { getDataTestIdElement } from "../../helpers";
import { clickTestItemButton } from "../../steps/ordering";
import { createUser, logUserOn } from "../../steps/users";

describe("When a user reloads the page after initiating a payment", () => {
  it("the item buttons are not disabled", () => {
    const username = `CypressUser${Date.now()}`;
    cy.visit("/");
    createUser(username);
    logUserOn(username);
    clickTestItemButton();
    getDataTestIdElement("item_pay_now").click();
    getDataTestIdElement("stripe_dialog_close");
    cy.reload();
    getDataTestIdElement("order_item_button").first().click();
    getDataTestIdElement("item_pay_now").should("have.prop", "disabled", false);
  });
});
