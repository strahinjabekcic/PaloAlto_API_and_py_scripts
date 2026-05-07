# PaloAlto_API_and_py_scripts
Repository containing Python automation scripts, API examples, and implementation guides for Palo Alto Networks, Prisma Strata Cloud Manager, and SD-WAN environments.
I have created few scripts without automating reading values from the files, excel tables etc, and you can use it like I have used it. I am planning to upgrade this in the future.
This repo will also contain the API calls without scripts, so you can use it to create your own scripts.

First of all I want to emphasise that there are two main pages about APIs, one is for the Strata Cloud Manager APIs, like object creation, fw rules creation etc, service routing etc, and the second page is about the SD-WAN part where you can manage your remote networks sites, creating DHCP scopes, routing, monitoring and a lot of different stuff.

First page Strata Cloud Manager APIs is https://pan.dev/scm/docs/home/ and the second one is https://pan.dev/sdwan/api/ where you can choose between the unified and legacy API, and I have choosen the unified because it is more the future proof. What is the difference on the very beggining is that you need to make call to the /sdwan/v2.1/api/profile immediately after creating access token.

For you to be able to use the APIs which you will probably later use in the some scripts, you need first to create service account on your Palo Alto SCM tenant. You are doing it like creating an access for the user in Identity and access management with difference you need to choose the service account Identity Type.
