"""
Code for tying SPARQL Engine into RDFLib

These should be automatically registered with RDFLib

"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Union

from rdflib.graph import Graph
from rdflib.plugins.sparql.algebra import translateQuery, translateUpdate
from rdflib.plugins.sparql.evaluate import evalQuery
from rdflib.plugins.sparql.parser import parseQuery, parseUpdate
from rdflib.plugins.sparql.sparql import Query, Update
from rdflib.plugins.sparql.update import evalUpdate
from rdflib.query import Processor, Result, UpdateProcessor
from rdflib.term import Identifier


def prepareQuery(
    queryString: str, initNs: Mapping[str, Any] = {}, base: Optional[str] = None
) -> Query:
    """
    Parse and translate a SPARQL Query
    """
    ret = translateQuery(parseQuery(queryString), base, initNs)
    ret._original_args = (queryString, initNs, base)
    return ret


def prepareUpdate(
    updateString: str, initNs: Mapping[str, Any] = {}, base: Optional[str] = None
) -> Update:
    """
    Parse and translate a SPARQL Update
    """
    ret = translateUpdate(parseUpdate(updateString), base, initNs)
    ret._original_args = (updateString, initNs, base)
    return ret


def processUpdate(
    graph: Graph,
    updateString: str,
    initBindings: Mapping[str, Identifier] = {},
    initNs: Mapping[str, Any] = {},
    base: Optional[str] = None,
) -> None:
    """
    Process a SPARQL Update Request
    returns Nothing on success or raises Exceptions on error
    """
    evalUpdate(
        graph, translateUpdate(parseUpdate(updateString), base, initNs), initBindings
    )


class SPARQLResult(Result):
    def __init__(self, res: Mapping[str, Any]):
        Result.__init__(self, res["type_"])
        self.vars = res.get("vars_")
        # type error: Incompatible types in assignment (expression has type "Optional[Any]", variable has type "MutableSequence[Mapping[Variable, Identifier]]")
        self.bindings = res.get("bindings")  # type: ignore[assignment]
        self.askAnswer = res.get("askAnswer")
        self.graph = res.get("graph")


class SPARQLUpdateProcessor(UpdateProcessor):
    def __init__(self, graph):
        self.graph = graph

    def update(
        self,
        strOrQuery: Union[str, Update],
        initBindings: Mapping[str, Identifier] = {},
        initNs: Mapping[str, Any] = {},
    ) -> None:
        if isinstance(strOrQuery, str):
            strOrQuery = translateUpdate(parseUpdate(strOrQuery), initNs=initNs)

        return evalUpdate(self.graph, strOrQuery, initBindings)


class SPARQLProcessor(Processor):
    def __init__(self, graph):
        self.graph = graph

    # NOTE on type error: this is because the super type constructor does not
    # accept base argument and thie position of the DEBUG argument is
    # different.
    # type error: Signature of "query" incompatible with supertype "Processor"
    def query(  # type: ignore[override]
        self,
        strOrQuery: Union[str, Query],
        initBindings: Mapping[str, Identifier] = {},
        initNs: Mapping[str, Any] = {},
        base: Optional[str] = None,
        DEBUG: bool = False,
    ) -> Mapping[str, Any]:
        """
        Evaluate a query with the given initial bindings, and initial
        namespaces. The given base is used to resolve relative URIs in
        the query and will be overridden by any BASE given in the query.
        """

        if not isinstance(strOrQuery, Query):
            parsetree = parseQuery(strOrQuery)
            query = translateQuery(parsetree, base, initNs)
        else:
            query = strOrQuery
        return evalQuery(self.graph, query, initBindings, base)
