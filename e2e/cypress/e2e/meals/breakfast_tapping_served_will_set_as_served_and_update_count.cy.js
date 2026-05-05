import { getDataTestIdElement } from "../../helpers";
import { getTotalServedInt } from "../../steps/meals";
import { createBreakfastOrderApi, generateReceiver } from "../../steps/orders";
import { createGuestUserApi, generateUsername } from "../../steps/users";

describe(
  "When an admin user clicks served for a breakfast meal",
  { testIsolation: false },
  () => {
    const username = generateUsername();
    const receiver = generateReceiver(username);

    it("it will show as served and increment the served count", function () {
      createGuestUserApi(username);
      createBreakfastOrderApi(username, receiver);
      cy.visit("/admin/breakfast");
      cy.contains(receiver, { timeout: 60000 });
      getDataTestIdElement("total-served").invoke("text").as("totalServed");
      getDataTestIdElement("meal-row")
        .filter(`:contains(${receiver})`)
        .find(`[data-testid=served-button]`)
        .then(($servedButtonEl) => {
          expect($servedButtonEl).to.have.text("✖️");
          cy.wrap($servedButtonEl).click().should("have.text", "✅");
          getDataTestIdElement("total-served").should(
            "have.text",
            `Total served: ${getTotalServedInt(this.totalServed) + 1}`,
            { timeout: 60000 },
          );
        });
    });

    it("and when clicked again it will show as not served and decrement the served count", function () {
      getDataTestIdElement("total-served").invoke("text").as("totalServed");
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
        });
    });
  },
);
