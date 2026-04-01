import { getDataTestIdElement } from "../../helpers";
import { clickTestItemButton } from "../../steps/ordering";
import { assertStripeDialogNotVisibleBeforeItemPayButton } from "../../steps/stripe";
import { createUserAPI, generateUsername, logUserOn } from "../../steps/users";

describe("When a user closes the stripe payment dialog when ordering an item", () => {
  it("does not reopening the stripe payment dialog", () => {
    const username = generateUsername();
    createUserAPI(username);
    cy.visit("/");
    logUserOn(username);
    clickTestItemButton();
    getDataTestIdElement("item_pay_now").click();
    getDataTestIdElement("stripe_qr_code_image");
    getDataTestIdElement("stripe_dialog_close").click();
    clickTestItemButton();
    assertStripeDialogNotVisibleBeforeItemPayButton();
  });
});
