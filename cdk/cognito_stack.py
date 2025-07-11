# Standard Library
from typing import Optional, Dict, Any

# Third Party
from aws_cdk import (
    NestedStack,
    aws_cognito as cognito,
)
from constructs import Construct

# Local Modules
from cdk.custom_constructs import CognitoAdminUser, CustomCognitoUserPool


class CognitoStack(NestedStack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        name: str,
        admin_email: str,
        admin_username: str,
        admin_password_secret_name: str,
        stack_suffix: Optional[str] = "",
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self.stack_suffix = (stack_suffix if stack_suffix else "").lower()

        # 1. Create the Cognito User Pool
        self.user_pool = self.create_cognito_user_pool(
            construct_id=f"DefaultUserPool{self.stack_suffix}",
            name=name,
        ).user_pool

        # 2. Create a User Pool Client for the application
        self.user_pool_client = self.user_pool.add_client(
            "AppClient",
            auth_flows=cognito.AuthFlow(admin_user_password=True),
            user_pool_client_name=f"{name}-app-client",
        )

        # 3. Use the custom construct to create the admin user
        _admin_user = CognitoAdminUser(
            self,
            "CognitoAdminUser",
            user_pool=self.user_pool,
            admin_username=admin_username,
            admin_email=admin_email,
            admin_password_secret_name=admin_password_secret_name,
        )

        # 4. Create the 'Admins' group in the User Pool
        self.admins_group = cognito.CfnUserPoolGroup(
            self,
            "AdminsGroup",
            group_name="admins",
            user_pool_id=self.user_pool.user_pool_id,
            description="Group for Arcane Scribe administrators",
            precedence=1,  # Ensure this group has precedence over others
        )

        # 4b. Create the 'Users' group in the User Pool
        self.users_group = cognito.CfnUserPoolGroup(
            self,
            "UsersGroup",
            group_name="users",
            user_pool_id=self.user_pool.user_pool_id,
            description="Group for Arcane Scribe users",
            precedence=2,  # Ensure this group has lower precedence than 'Admins'
        )

        # 5. Add the admin user to the 'Admins' group
        _add_admin_to_group = cognito.CfnUserPoolUserToGroupAttachment(
            self,
            "AdminUserGroupAttachment",
            group_name=self.admins_group.group_name,
            user_pool_id=self.user_pool.user_pool_id,
            username=admin_username,
        )

        # 6. Add a unique domain prefix for our User Pool
        self.user_pool_domain = self.user_pool.add_domain(
            "CognitoDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"arcane-scribe-users{self.stack_suffix}"
            )
        )

        # This dependency ensures the user is created before we try to add them to a group
        _add_admin_to_group.add_dependency(_admin_user.get_resource())

        # Outputs from the nested stack
        self.user_pool_id = self.user_pool.user_pool_id
        self.user_pool_client_id = self.user_pool_client.user_pool_client_id

    def create_cognito_user_pool(
        self,
        construct_id: str,
        name: str,
        self_sign_up_enabled: Optional[bool] = False,
        sign_in_aliases: Optional[Dict[str, Any]] = None,
        auto_verify: Optional[Dict[str, Any]] = None,
        standard_attributes: Optional[Dict[str, Any]] = None,
        password_policy: Optional[Dict[str, Any]] = None,
    ) -> CustomCognitoUserPool:
        """Helper method to create a Cognito User Pool.

        Parameters
        ----------
        construct_id : str
            The ID of the construct.
        name : str
            The name of the Cognito User Pool.
        self_sign_up_enabled : Optional[bool], optional
            Whether self sign-up is enabled, by default False
        sign_in_aliases : Optional[Dict[str, Any]], optional
            Sign-in aliases for the user pool, by default None
        auto_verify : Optional[Dict[str, Any]], optional
            Auto-verified attributes for the user pool, by default None
        standard_attributes : Optional[Dict[str, Any]], optional
            Standard attributes for the user pool, by default None
        password_policy : Optional[Dict[str, Any]], optional
            Password policy for the user pool, by default None
        account_recovery : Optional[str], optional
            Account recovery method, by default "EMAIL_ONLY"

        Returns
        -------
        CustomCognitoUserPool
            The created Cognito User Pool instance.
        """
        custom_cognito_user_pool = CustomCognitoUserPool(
            scope=self,
            id=construct_id,
            name=name,
            stack_suffix=self.stack_suffix,
            self_sign_up_enabled=self_sign_up_enabled,
            sign_in_aliases=sign_in_aliases,
            auto_verify=auto_verify,
            standard_attributes=standard_attributes,
            password_policy=password_policy
        )
        return custom_cognito_user_pool
