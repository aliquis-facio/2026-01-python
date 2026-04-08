# https://www.acmicpc.net/problem/7569

import sys
from collections import deque

input = sys.stdin.readline

# 6 방향
DIRECTIONS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
# 가로, 세로, 높이
M, N, H = map(int, input().split(" "))
# 3차원 배열
space = []
# 익은 토마토 좌표 배열
q = deque()
# 안 익은 토마토 갯수
cnt = 0

for h in range(H):
    mat = []
    for n in range(N):
        row = list(map(int, input().split()))
        mat.append(row)
        for m in range(M):
            # 익은 토마토 좌표 수집
            if row[m] == 1:
                q.append((h, n, m))
            # 안 익은 토마토 갯수 세기
            elif row[m] == 0:
                cnt += 1
    space.append(mat)

# BFS
def solve():
    global cnt

    # 안 익은 토마토가 없을 때
    if cnt == 0:
        return 0
    
    max_day = 0

    while q:
        x, y, z = q.popleft()

        for dx, dy, dz in DIRECTIONS:
            nx = x+dx
            ny = y+dy
            nz = z+dz

            # index error 방지
            if 0 <= nx < H and 0 <= ny < N and 0 <= nz < M:
                # 미방문
                if space[nx][ny][nz] == 0:
                    q.append((nx, ny, nz))
                    cnt -= 1
                    # 최댓값 갱신
                    space[nx][ny][nz] = space[x][y][z] + 1
                    max_day = max(max_day, space[nx][ny][nz])
    
    if cnt > 0:
        return -1
    
    return max_day - 1

# 출력
print(solve())