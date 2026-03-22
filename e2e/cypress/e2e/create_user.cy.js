import { createUser, logUserOn } from "../steps/users";

describe("When signing up a new user", () => {
  it("is created successfully", () => {
    const username = `CypressUser${Date.now()}`;
    cy.visit("/");
    createUser(username)
    logUserOn(username)
    cy.get(`[data-testid="user-page-heading"]`).contains(`Hello ${username}`);
  });
});
