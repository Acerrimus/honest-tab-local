describe("When the endpoint api/test/user is called", () => {
  it("should create a new user in the database", () => {
    cy.request({
      method: "POST",
      url: "http://app:8000/api/test/user",
    }).then((response) => {
      expect(response.status).to.eq(201);
    });
  });
});
