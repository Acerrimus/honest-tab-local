import { getDataTestIdElement } from "../../helpers";
import {
  getTotalServedInt,
  waitForReceiverServedStatusAndTotalCountToRender,
} from "../../steps/meals";
import { createDinnerOrderApi, generateReceiver } from "../../steps/orders";
import { createGuestUserApi, generateUsername } from "../../steps/users";

describe("When an admin user clicks served for a guest's dinner meal", () => {
  const username = generateUsername();
  const receiver = generateReceiver(username)

  it("it will show as served and increment the guests served count with the volunteers served count staying the same", function () {
    createGuestUserApi(username);
    createDinnerOrderApi(username, receiver);
    cy.visit("/admin/dinner");
    cy.contains(receiver, {timeout: 60000});
    getDataTestIdElement("total-served").invoke("text").as("totalServed");
    getDataTestIdElement("total-guests-served")
      .invoke("text")
      .as("totalGuestsServed");
    getDataTestIdElement("total-volunteers-served")
      .invoke("text")
      .as("totalVolunteersServed");
    getDataTestIdElement("meal-row")
      .filter(`:contains(${receiver})`)
      .find(`[data-testid=served-button]`)
      .then(($servedButtonEl) => {
        expect($servedButtonEl).to.have.text("✖️");
        cy.wrap($servedButtonEl).click().should("have.text", "✅");
        getDataTestIdElement("total-served").should(
          "have.text",
          `Total served: ${getTotalServedInt(this.totalServed) + 1}`,{timeout: 60000}
        );
        getDataTestIdElement("total-volunteers-served").should(
          "have.text",
          this.totalVolunteersServed,
        );
        getDataTestIdElement("total-guests-served").should(
          "have.text",
          `Total served: ${getTotalServedInt(this.totalGuestsServed) + 1}`,
        );
      });
  });

  it("and when clicked again it will show as not served and decrement the guests served count with the volunteers served count staying the same", function () {
    cy.visit("/admin/dinner");
    waitForReceiverServedStatusAndTotalCountToRender(receiver);
    getDataTestIdElement("total-served").invoke("text").as("totalServed");
    getDataTestIdElement("total-guests-served")
      .invoke("text")
      .as("totalGuestsServed");
    getDataTestIdElement("total-volunteers-served")
      .invoke("text")
      .as("totalVolunteersServed");
    getDataTestIdElement("meal-row")
      .filter(`:contains(${receiver})`)
      .find(`[data-testid=served-button]`)
      .then(($servedButtonEl) => {
        expect($servedButtonEl).to.have.text("✅");
        cy.wrap($servedButtonEl).click().should("have.text", "✖️");
        getDataTestIdElement("total-served").should(
          "have.text",
          `Total served: ${getTotalServedInt(this.totalServed) - 1}`,
        );
        getDataTestIdElement("total-volunteers-served").should(
          "have.text",
          this.totalVolunteersServed,
        );
        getDataTestIdElement("total-guests-served").should(
          "have.text",
          `Total served: ${getTotalServedInt(this.totalGuestsServed) - 1}`,
        );
      });
  });
});
