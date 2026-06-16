"""FAQ 크롤러 공통 기반 클래스."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import requests

from faq_crawling.constants import DEFAULT_HEADERS


class CrawlerError(RuntimeError):
    """크롤링 중 처리 가능한 오류를 표현하는 예외."""


class BaseCrawler(ABC):
    """사이트별 크롤러가 공통으로 따르는 기본 구조.

    각 사이트 크롤러는 검색 URL 생성, 목록 수집, 상세 수집 방식이 다릅니다.
    그래서 공통 요청 처리만 여기서 제공하고 실제 파싱은 하위 클래스에서 구현합니다.
    """

    source_name: str
    category: str

    def __init__(
        self,
        *,
        timeout: int = 10,
        headers: dict[str, str] | None = None,
    ) -> None:
        # 요청 제한 시간과 HTTP 헤더를 인스턴스 설정으로 보관합니다.
        self.timeout = timeout
        self.headers = headers or DEFAULT_HEADERS

    def safe_get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        """GET 요청을 보내고 실패하면 CrawlerError로 변환합니다."""
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as exc:
            raise CrawlerError(f"요청에 실패했습니다: {url}") from exc

    @abstractmethod
    def build_search_url(self, keyword: str, page: int = 0) -> str:
        """검색어와 페이지 번호로 검색 URL을 만듭니다."""

    @abstractmethod
    def crawl_list(self, keyword: str, page: int = 0) -> list[str]:
        """검색 결과 페이지에서 상세 게시글 URL 목록을 수집합니다."""

    @abstractmethod
    def crawl_detail(self, url: str) -> dict[str, Any]:
        """상세 게시글 페이지에서 제목, 본문, 작성일 등을 수집합니다."""

    def crawl(
        self,
        keyword: str,
        *,
        page_limit: int = 1,
        detail_limit: int = 20,
    ) -> list[dict[str, Any]]:
        """검색어 하나에 대한 목록 수집과 상세 수집을 순서대로 실행합니다."""
        detail_urls: list[str] = []

        # 클리앙은 첫 페이지가 p=0부터 시작합니다.
        for page in range(page_limit):
            detail_urls.extend(self.crawl_list(keyword, page=page))

        # 여러 검색 결과에서 같은 글이 나올 수 있으므로 URL 기준으로 한 번 제거합니다.
        unique_urls = list(dict.fromkeys(detail_urls))[:detail_limit]

        results: list[dict[str, Any]] = []

        # 상세 페이지 하나가 실패해도 전체 크롤링은 계속 진행합니다.
        for detail_url in unique_urls:
            try:
                results.append(self.crawl_detail(detail_url))
            except CrawlerError:
                continue

        return results
