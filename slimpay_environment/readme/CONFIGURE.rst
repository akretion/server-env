With this module installed, account_payment_slimpay the are
configured in encrypted data thanks to server_environment_data_encryption `` module (which is a module
you should provide, see the documentation of `server_environment` for
more information).

In the configuration file of each environment, you may first use the
section `[slimpay_payment_acquirer]`.

Then for each server, you can define additional values or override the
default values with a section named `[slimpay_payment_acquirer.resource_name]` where "resource_name" is the name of the server.

Example of config file ::

  [slimpay_payment_acquirer]
  # here is the default format
  slimpay_api_url = 'ZPL'

  [slimpay_payment_acquirer.prod_server]
  slimpay_creditor = prod_account
  slimpay_app_id = ixhy5yu8yulk7
  slimpay_app_secret = 123promenons-nous-dans-les-bois456cueillir-des-saucisses


  [carrier_account.test_server]
  slimpay_creditor = test_account
  slimpay_app_id = iAERFHTTGTG788
  slimpay_app_secret = Allez-dans-les-bois456cueillir-des-saucisses-sil-y-en-a
