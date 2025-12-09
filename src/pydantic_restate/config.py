import typing
from datetime import timedelta
from typing import Dict

import restate
from pydantic import BaseModel, Field
from restate.serde import DefaultSerde, Serde


class BaseSettings(BaseModel):
    identity_keys: list[str] = Field(default_factory=list)


class BaseServiceOptions(BaseModel):
    metadata: Dict[str, str] | None = Field(
        default=None,
        description="Metadata, as propagated in the Admin REST API.",
    )
    inactivity_timeout: timedelta | None = Field(
        default=None,
        description=(
            "This timer guards against stalled invocations. Once it expires, Restate triggers a graceful"
            "termination by asking the invocation to suspend (which preserves intermediate progress)."
            "The abortTimeout is used to abort the invocation, in case it doesn't react to the request to suspend."
            "This overrides the default inactivity timeout configured in the restate-server for all invocations."
        ),
    )
    abort_timeout: timedelta | None = Field(
        default=None,
        description=(
            "This timer guards against stalled service/handler invocations that are supposed to terminate. The"
            "abort timeout is started after the inactivityTimeout has expired and the service/handler invocation has been asked to gracefully terminate."
            "Once the timer expires, it will abort the service/handler invocation."
            "This timer potentially *interrupts* user code. If the user code needs longer to gracefully terminate, then this value needs to be set accordingly."
            "This overrides the default abort timeout configured in the restate-server for all invocations."
        ),
    )
    journal_retention: timedelta | None = Field(
        default=None,
        description=(
            "The journal retention."
            "In case the request has an idempotency key, the idempotencyRetention caps the journal retention time."
        ),
    )
    idempotency_retention: timedelta | None = Field(
        default=None,
        description="The retention duration of idempotent requests.",
    )
    ingress_private: bool | None = Field(
        default=None,
        description=(
            "When set to True, it cannot be invoked from the restate-server"
            "HTTP and Kafka ingress, but only from other services."
        ),
    )
    invocation_retry_policy: restate.InvocationRetryPolicy | None = Field(
        default=None,
        description="The retry policy for failed invocations.",
    )


class ServiceOptions(BaseServiceOptions):
    name: str = Field(description="Name of the service")
    description: str | None = Field(
        default=None,
        description="Documentation as shown in the UI, Admin REST API, and the generated OpenAPI documentation.",
    )

    def new_service(self) -> restate.Service:
        return restate.Service(
            self.name,
            description=self.description,
            metadata=self.metadata,
            inactivity_timeout=self.inactivity_timeout,
            abort_timeout=self.abort_timeout,
            journal_retention=self.journal_retention,
            idempotency_retention=self.idempotency_retention,
            ingress_private=self.ingress_private,
            invocation_retry_policy=self.invocation_retry_policy,
        )


class ServiceHandlerOptions(BaseServiceOptions):
    name: str | None = Field(default=None, description="Name of the handler")

    def handler(
        self,
        service: restate.Service,
        accept: str = "application/json",
        content_type: str = "application/json",
        input_serde: Serde[restate.service.I] = DefaultSerde(),
        output_serde: Serde[restate.service.O] = DefaultSerde(),
    ) -> typing.Callable[[restate.service.T], restate.service.T]:
        return service.handler(
            name=self.name,
            accept=accept,
            content_type=content_type,
            input_serde=input_serde,
            output_serde=output_serde,
            metadata=self.metadata,
            inactivity_timeout=self.inactivity_timeout,
            abort_timeout=self.abort_timeout,
            journal_retention=self.journal_retention,
            idempotency_retention=self.idempotency_retention,
            ingress_private=self.ingress_private,
            invocation_retry_policy=self.invocation_retry_policy,
        )
