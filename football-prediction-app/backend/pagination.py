"""
Pagination utilities for Football Prediction App
Provides consistent pagination across all API endpoints
"""

from typing import Dict, Any, List, Optional, Tuple
from flask import request, url_for
from sqlalchemy.orm import Query
from dataclasses import dataclass
import math


@dataclass
class PaginationParams:
    """Pagination parameters"""
    page: int = 1
    per_page: int = 20
    max_per_page: int = 100
    
    @classmethod
    def from_request(cls, default_per_page: int = 20):
        """Create pagination params from request"""
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', default_per_page))
            
            # Validate values
            page = max(1, page)
            per_page = max(1, min(per_page, cls.max_per_page))
            
            return cls(page=page, per_page=per_page)
        except (ValueError, TypeError):
            return cls(page=1, per_page=default_per_page)


class Paginator:
    """Paginator for SQLAlchemy queries"""
    
    def __init__(self, query: Query, page: int = 1, per_page: int = 20):
        self.query = query
        self.page = max(1, page)
        self.per_page = max(1, min(per_page, 100))
        self._total = None
    
    @property
    def total(self) -> int:
        """Get total number of items"""
        if self._total is None:
            self._total = self.query.count()
        return self._total
    
    @property
    def pages(self) -> int:
        """Get total number of pages"""
        return math.ceil(self.total / self.per_page)
    
    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page"""
        return self.page > 1
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page"""
        return self.page < self.pages
    
    @property
    def prev_page(self) -> Optional[int]:
        """Get previous page number"""
        return self.page - 1 if self.has_prev else None
    
    @property
    def next_page(self) -> Optional[int]:
        """Get next page number"""
        return self.page + 1 if self.has_next else None
    
    def get_items(self) -> List[Any]:
        """Get items for current page"""
        offset = (self.page - 1) * self.per_page
        return self.query.offset(offset).limit(self.per_page).all()
    
    def get_page_info(self) -> Dict[str, Any]:
        """Get pagination metadata"""
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'pages': self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_page': self.prev_page,
            'next_page': self.next_page
        }
    
    def get_links(self, endpoint: str, **kwargs) -> Dict[str, Optional[str]]:
        """Get pagination links"""
        links = {
            'self': url_for(endpoint, page=self.page, per_page=self.per_page, **kwargs),
            'first': url_for(endpoint, page=1, per_page=self.per_page, **kwargs),
            'last': url_for(endpoint, page=self.pages, per_page=self.per_page, **kwargs) if self.pages > 0 else None,
            'prev': None,
            'next': None
        }
        
        if self.has_prev:
            links['prev'] = url_for(endpoint, page=self.prev_page, 
                                  per_page=self.per_page, **kwargs)
        
        if self.has_next:
            links['next'] = url_for(endpoint, page=self.next_page, 
                                  per_page=self.per_page, **kwargs)
        
        return links


def paginate_query(query: Query, page: int = None, per_page: int = None) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        Tuple of (items, pagination_info)
    """
    # Get pagination params from request if not provided
    if page is None or per_page is None:
        params = PaginationParams.from_request()
        page = page or params.page
        per_page = per_page or params.per_page
    
    paginator = Paginator(query, page, per_page)
    items = paginator.get_items()
    pagination_info = paginator.get_page_info()
    
    return items, pagination_info


def paginated_response(query: Query, serializer=None, endpoint: str = None, 
                      **kwargs) -> Dict[str, Any]:
    """
    Create a paginated response
    
    Args:
        query: SQLAlchemy query object
        serializer: Function to serialize items (optional)
        endpoint: Endpoint name for generating links
        **kwargs: Additional arguments for URL generation
    
    Returns:
        Dictionary with data and pagination info
    """
    params = PaginationParams.from_request()
    paginator = Paginator(query, params.page, params.per_page)
    
    items = paginator.get_items()
    
    # Serialize items if serializer provided
    if serializer:
        data = [serializer(item) for item in items]
    else:
        data = items
    
    response = {
        'data': data,
        'pagination': paginator.get_page_info()
    }
    
    # Add links if endpoint provided
    if endpoint:
        response['links'] = paginator.get_links(endpoint, **kwargs)
    
    return response


def offset_paginate(items: List[Any], offset: int = 0, limit: int = 20) -> Dict[str, Any]:
    """
    Simple offset-based pagination for lists
    
    Args:
        items: List of items to paginate
        offset: Number of items to skip
        limit: Maximum number of items to return
    
    Returns:
        Dictionary with paginated data
    """
    total = len(items)
    offset = max(0, offset)
    limit = max(1, min(limit, 100))
    
    paginated_items = items[offset:offset + limit]
    
    return {
        'data': paginated_items,
        'pagination': {
            'offset': offset,
            'limit': limit,
            'total': total,
            'returned': len(paginated_items),
            'has_more': offset + limit < total
        }
    }


def cursor_paginate(query: Query, cursor: Optional[str] = None, 
                   limit: int = 20, order_by='id') -> Dict[str, Any]:
    """
    Cursor-based pagination for efficient large dataset navigation
    
    Args:
        query: SQLAlchemy query object
        cursor: Cursor value (usually an ID)
        limit: Maximum number of items to return
        order_by: Field to order by (must be unique and sequential)
    
    Returns:
        Dictionary with paginated data and next cursor
    """
    limit = max(1, min(limit, 100))
    
    # Apply cursor if provided
    if cursor:
        try:
            cursor_value = int(cursor)
            query = query.filter(f"{order_by} > {cursor_value}")
        except (ValueError, TypeError):
            pass
    
    # Order by the cursor field
    query = query.order_by(order_by)
    
    # Get one extra item to check if there's more
    items = query.limit(limit + 1).all()
    
    has_more = len(items) > limit
    if has_more:
        items = items[:-1]  # Remove the extra item
    
    # Get next cursor from last item
    next_cursor = None
    if items and has_more:
        last_item = items[-1]
        next_cursor = str(getattr(last_item, order_by))
    
    return {
        'data': items,
        'pagination': {
            'limit': limit,
            'cursor': cursor,
            'next_cursor': next_cursor,
            'has_more': has_more
        }
    }


# Decorators for easy pagination
def paginate(default_per_page: int = 20):
    """
    Decorator to add pagination to route handlers
    
    Usage:
        @app.route('/api/teams')
        @paginate(default_per_page=50)
        def get_teams():
            query = Team.query
            return query  # Return query, decorator handles pagination
    """
    def decorator(f):
        def wrapped(*args, **kwargs):
            # Get the query from the route handler
            result = f(*args, **kwargs)
            
            if isinstance(result, Query):
                # If it's a query, paginate it
                params = PaginationParams.from_request(default_per_page)
                return paginated_response(
                    result, 
                    endpoint=request.endpoint,
                    **request.view_args
                )
            else:
                # Otherwise, return as-is
                return result
        
        wrapped.__name__ = f.__name__
        return wrapped
    
    return decorator