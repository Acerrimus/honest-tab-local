import { getDataTestIdElement } from "../helpers";

describe("When loading the homepage", () => {
  it("loads successfully", () => {
    cy.visit("/")
    getDataTestIdElement("title").contains("Olive Branch")
  });
});