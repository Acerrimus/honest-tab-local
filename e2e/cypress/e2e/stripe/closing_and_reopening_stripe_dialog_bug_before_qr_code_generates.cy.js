import { getDataTestIdElement } from "../../helpers";
import { clickTestItemButton } from "../../steps/ordering";
import { assertStripeDialogNotVisibleBeforeItemPayButton } from "../../steps/stripe";
import { createUser, logUserOn } from "../../steps/users";

describe("When a user closes the stripe payment dialog when ordering an item before the qr code generates", () => {
  it("it does not reopen the stripe payment dialog", () => {
    const username = `CypressUser${Date.now()}`;
    cy.visit("/");
    createUser(username);
    logUserOn(username);
    clickTestItemButton();
    getDataTestIdElement("item_pay_now").click();
    getDataTestIdElement("stripe_dialog_close").click();
    getDataTestIdElement("stripe_dialog_close").should("not.exist");
    clickTestItemButton();
    assertStripeDialogNotVisibleBeforeItemPayButton();
  });
});
