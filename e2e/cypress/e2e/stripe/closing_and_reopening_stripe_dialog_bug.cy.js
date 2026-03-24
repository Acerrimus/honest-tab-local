import { getDataTestIdElement } from "../../helpers";
import { clickTestItemButton } from "../../steps/ordering";
import { createUser, logUserOn } from "../../steps/users";

describe("When a user closes the stripe payment dialog when ordering an item", () => {
  it("does not reopening the stripe payment dialog", () => {
    const username = `CypressUser${Date.now()}`;
    cy.visit("/");
    createUser(username);
    logUserOn(username);
    clickTestItemButton();
    getDataTestIdElement("item_pay_now").click();
    getDataTestIdElement("stripe_qr_code_image");
    getDataTestIdElement("stripe_dialog_close").click();
    clickTestItemButton();
    getDataTestIdElement("item_pay_now").click();
    getDataTestIdElement("stripe_dialog_title").should("not.exist");
  });
});
