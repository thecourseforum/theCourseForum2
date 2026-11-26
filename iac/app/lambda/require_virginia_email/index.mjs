const UVA_EMAIL = /^[a-z]{2,3}[0-9][a-z]{1,3}@virginia\.edu$/;

export const handler = async (event) => {
  const email = event.request.userAttributes.email.trim().toLowerCase();
  if (!UVA_EMAIL.test(email)) {
    throw new Error('Email must be a UVA computing ID @virginia.edu address (e.g. mst3k@virginia.edu)');
  }
  return event;
};
