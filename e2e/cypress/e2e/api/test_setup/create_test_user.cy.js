import { createUserAPI, generateUsername } from "../../../steps/users";

describe("When the endpoint api/test/user is called", () => {
  it("should create a new user in the database", () => {
    createUserAPI(generateUsername()).then((response) => {
      expect(response.status).to.eq(201);
    });
  });
});
